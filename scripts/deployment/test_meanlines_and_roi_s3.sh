# #!/bin/sh

# # invokes a meanline/roi test on an image
# #
# #   sh test_meanlines_and_roi_s3.sh <image_name> <full_image_path> [dev]
# #
# # if the third argument is "dev", the data is copied locally.
# # otherwise it's copied to the s3 metadata bucket.

# # "xxxxxx_xxxx_xxxx_xx.png"
# image_name=$1
# # full path to the image
# image_path=$2
# # "dev" is development, everything else is production
# type=$3

# dir=`mktemp -d /tmp/seismo.XXXXX` && \
# echo "writing to $dir" && \
# sh set_seismo_status.sh $image_name 0 && \
# python test_meanlines_and_roi.py --image "$image_path" --output "$dir" --stats stats.json && \
# # sh copy_to_s3.sh $image_name $dir metadata $type && \
# sh set_seismo_status.sh $image_name 3 && \
# rm -rf $dir

#!/bin/sh

# Usage: sh test_meanlines_and_roi_s3.sh <image_name> <full_image_path> [dev]

image_name=$1
image_path=$2
type=$3

# Make temp directory
dir=`mktemp -d /tmp/seismo.XXXXX`
echo "writing to $dir"

# Run the processing Python script
sh set_seismo_status.sh $image_name 0

# Use PROJECT_ROOT to point to tests/ folder
ROOT_DIR=${PROJECT_ROOT:-"../.."}
python3 "$ROOT_DIR/tests/test_meanlines_and_roi.py" --image "$image_path" --output "$dir" --stats stats.json

sh set_seismo_status.sh $image_name 3

# ===== COPY TO LOCAL FOLDER =====
# Create local output directory
local_out_dir="$ROOT_DIR/outputs/${image_name%.*}"  # remove .png extension
mkdir -p "$local_out_dir"

# Copy everything from tmp dir to local output folder
cp "$dir"/* "$local_out_dir/"

echo "Results saved to $local_out_dir"

# Optional: remove tmp folder
rm -rf $dir
