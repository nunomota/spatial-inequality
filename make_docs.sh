BUILD_DIR='../docs'

cd spatial_inequality/ ;
rm -r $BUILD_DIR/* ;
pdoc3 --force --html . -o $BUILD_DIR -c latex_math=True ;
mv $BUILD_DIR/spatial_inequality/* $BUILD_DIR ;
rm -r $BUILD_DIR/spatial_inequality ;
cd ..