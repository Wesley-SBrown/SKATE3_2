import numpy as np
from numpy.typing import NDArray
from typing import Union, Optional, Any
from geojson import LineString, Feature
from .utilities import linear_fit
from geojson import Feature

class segment:
    """
    A segment is a region of pixels and a center line that
    represents that region.

    """

    def __init__(
        self, 
        coords: NDArray[np.intp], 
        values: NDArray[np.generic], 
        id: Union[int, str], 
        ridge_line: Optional[NDArray[np.intp]] = None
    ) -> None:
        """
        Initialize a segment with pixel coordinates, values, an identifier, and an optional ridge line.

        Parameters
        ----------
        coords : NDArray[np.intp]
            The pixel coordinates belonging to the segment region
        values : NDArray[np.generic]
            The pixel values associated with the region
        id : Union[int, str]
            Unique identifier for the segment
        ridge_line : Optional[NDArray[np.integer]], optional
            An optional array of ridge line pixel coordinates
        """
        self.region = region(coords, values)
        self.set_linear_fit()
        self.id = id
        if ridge_line is not None:
            self.add_ridge_line(ridge_line)

    # def binary_image(self):
    #   return self.region.binary_image()

    def add_ridge_line(
        self, 
        pixel_coords: NDArray[np.intp]
    ) -> None:
        """
        Add a ridge line to the segment and compute its center line if sufficient points exist.

        Parameters
        ----------
        pixel_coords : NDArray[np.intp]
            The pixel coordinates defining the ridge line.
        """
        self.ridge_line = pixel_coords
        # self.set_pixel_series()
        if self.ridge_line.size > 2:
            self.set_center_line(self.ridge_line)
            self.has_center_line = True
        else:
            self.has_center_line = False

    def add_center_line_values(
        self, 
        values: NDArray[np.generic]
    ) -> None:
        """
        Assign values to the segment's center line

        Parameters
        ----------
        values : NDArray[np.generic]
            The values to assign to the center line
        """
        self.center_line.values = values

    def add_horizontal_ridges(
        self, 
        coords: NDArray[np.intp]
    ) -> None:
        """
        Add horizontal ridge coordinates to the segment

        Parameters
        ----------
        coords : NDArray[np.intp]
            Horizontal ridge pixel coordinates
        """
        self.ridge_line_h = coords

    def add_vertical_ridges(
        self, 
        coords: NDArray[np.intp]
    ) -> None:
        """
        Add vertical ridge coordinates to the segment

        Parameters
        ----------
        coords : NDArray[np.intp]
            Vertical ridge pixel coordinates
        """
        self.ridge_line_v = coords

    def to_geojson_feature(self) -> Feature:
        """
        Convert the segment's center line into a GeoJSON Feature with a LineString geometry

        Returns
        -------
        geojson.Feature
            A GeoJSON Feature object representing the center line
        """
        center_line = list(
            zip(list(map(int, self.center_line.x)), list(map(int, self.center_line.y)))
        )
        return Feature(geometry=LineString(center_line), id=self.id)

    def to_json_properties(self) -> dict[str, Any]:
        """
        These properties are needed in combination with the
        geojson to reconstruct complete segment objects. This is
        useful for debugging and for more advanced segment assignment.

        We store the properties separately from the geojson because
        the client only needs the geojson for rendering; it shouldn't
        have to download all the extra property cruft from the server.

        Returns
        -------
        dict[str, Any]
            A dictionary containing serialized region values and coordinate pairs
        """
        region_coords = list(
            zip(list(map(int, self.region.ii)), list(map(int, self.region.jj)))
        )
        properties = {"values": self.region.values.tolist(), "coords": region_coords}
        return properties

    # def set_pixel_series(self):
    #   self.pixel_series = ridge_line_to_series(self.ridge_line)
    #   #self.set_center_line()

    # def plot_ridge_line(self):
    #   scatter(self.ridge_line[:,1], (-self.ridge_line[:,0]))

    # def plot_pixel_series(self):
    #   scatter(self.pixel_series[:,1], (-self.pixel_series[:,0]))

    def set_linear_fit(self) -> None:
        """
        Compute and store the linear fit for the segment's region coordinates.
        """
        self.linear_fit = linear_fit(self.region.coords)

    def set_center_line(self, series: Any) -> None:
        """
        Compute and store the linear fit for the segment's region coordinates.
        """
        self.center_line = series_to_center_line(series)

    # def plot_center_line(self):
    #   plt.plot(self.center_line[:,1], (-self.center_line[:,0]), '-')


class region:
    """
    The coordinates of a collection of pixels.

    """

    # def __init__(self, pixel_coords, image_shape, region_ID=0):
    #   self.coords = pixel_coords
    #   self.ii = self.coords[:,0]
    #   self.jj = self.coords[:,1]
    #   self.dims = image_shape
    #   self.ID = region_ID
    #   self.calc_properties()
    #   self.create_binary()

    def __init__(
        self, 
        coords: NDArray[np.intp], 
        values: NDArray[np.generic]
    ) -> None:
        """
        Initialize a region with specific pixel coordinates and associated values

        Parameters
        ----------
        coords : NDArray[np.intp]
            The 2D coordinate array of pixels belonging to the region
        values : NDArray[np.generic]
            The values corresponding to each pixel in the region
        """
        self.coords = coords
        self.values = values
        self.ii = self.coords[:, 0]
        self.jj = self.coords[:, 1]
        
        self.region_domain = np.array([0, 0], dtype=int)
        self.region_range = np.array([0, 0], dtype=int)

        self.calc_properties()
        self.create_binary()

    def calc_properties(self) -> None:
        """
        Calculate region properties including domain, range, upper-left corner,
        centroid, size, height, width, and coordinate lookup set
        """
        # calculate domain, range, upper-left corner,
        # centroid, width, height, and size (i.e. number of pixels in region)
        self.region_domain[0] = np.amin(self.jj)
        self.region_domain[1] = np.amax(self.jj)
        self.region_range[0] = np.amin(self.ii)
        self.region_range[1] = np.amax(self.ii)
        self.ul_corner = np.array(
            [self.region_range[0], self.region_domain[0]], dtype=int
        )
        self.centroid = np.mean(self.coords, axis=0)
        self.size = self.coords.shape[0]
        self.height = self.region_range[1] - self.region_range[0] + 1
        self.width = self.region_domain[1] - self.region_domain[0] + 1
        self.coord_set = set(map(tuple, self.coords))

    def add_pixels(self, pixel_coords: NDArray[np.intp]) -> None:
        """
        Add new pixel coordinates to the region and recalculate its properties

        Parameters
        ----------
        pixel_coords : NDArray[np.intp]
            Pixel coordinates to add to the region
        """
        pixel_list = list(self.coords)
        pixel_list = pixel_list + list(pixel_coords)
        pixel_list = list(map(tuple, pixel_list))
        pixel_list = list(set(pixel_list))  # remove duplicates
        pixel_list = np.asarray(tuple(pixel_list), dtype=int)
        self.coords = pixel_list
        self.calc_properties()

    def remove_pixels(self, pixel_coords: NDArray[np.intp]) -> None:
        """
        Remove specified pixel coordinates from the region and recalculate its properties

        Parameters
        ----------
        pixel_coords : NDArray[np.intp]
            Pixel coordinates to remove from the region
        """
        curr_pixels = set(map(tuple, list(self.coords)))
        pixels_to_remove = set(map(tuple, list(pixel_coords)))
        new_pixel_list = curr_pixels - pixels_to_remove
        new_pixel_list = np.asarray(tuple(new_pixel_list), dtype=int)
        self.coords = new_pixel_list
        self.calc_properties()

    def create_binary(self) -> None:
        """
        Create boolean binary arrays representing the region and its bounding box mask.
        """
        # create two boolean arrays, one representing the region itself,
        # the other representing everything else in the bounding box that
        # contains the region
        ii_offset = self.ii - self.ul_corner[0]
        jj_offset = self.jj - self.ul_corner[1]
        self.binary = np.zeros((self.height, self.width), dtype=bool)
        self.binary[ii_offset, jj_offset] = True
        self.mask = ~self.binary

    # def binary_image(self):
    #   img = np.zeros(self.dims, dtype=bool)
    #   img[self.coords[:,0], self.coords[:,1]] = True
    #   #for p in self.coords:
    #   #    img[p[0], p[1]] = True
    #   return img

    def is_in_region(
        self, pixel_coords: Union[tuple[int, int], list[int], NDArray[np.intp]]
    ) -> bool:
        """
        Check whether given pixel coordinates reside within the region using optimized lookup

        Parameters
        ----------
        pixel_coords : Union[tuple[int, int], list[int], NDArray[np.intp]]
            The pixel coordinates to check

        Returns
        -------
        bool
            True if the coordinates belong to the region, False otherwise
        """
        # optimized lookup
        return tuple(pixel_coords) in self.coord_set

    def pixel_row(self, row: int) -> NDArray[np.integer]:
        """
        Retrieve all pixel coordinates in the region matching a specific row index

        Parameters
        ----------
        row : int
            The target row index (i-coordinate)

        Returns
        -------
        NDArray[np.integer]
            An array of pixel coordinates matching the specified row
        """
        return self.coords[(self.ii == row), :]

    def pixel_column(self, col):
        return self.coords[(self.jj == col), :]


"""
Turning off splining for now
"""


def series_to_center_line(series):
    return center_line(series)


class center_line:
    def __init__(self, series):
        self.coords = series
        self.x = series[:, 1]
        self.y = series[:, 0]
