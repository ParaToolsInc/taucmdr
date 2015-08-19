# Obviously, you should modify this accordingly.
# Jeff's Mac
#CXX = /Users/jhammond/eclipse/MPICH2/git/install-clang/bin/mpicxx
# ALCF Vesta (BGQ)
CXX = mpicxx
CXXFLAGS = -g -O2 -std=gnu++0x

# Symbolically link madness.r3267/src/lib/world to the directory in which you want to compile.
# Symbolically link madness.r3267/build/include/madness_config.h to the directory in which you want to compile.
INCLUDE = -I.
CXXFLAGS += $(INCLUDE)

# Copy libMADworld.a to the directory in which you want to link.
LIBS = -L. -lMADworld

# If you built MADNESS with TBB enabled, uncomment this line and modify the TBB path appropriately.
# Jeff's Mac
#BLAS = -framework Accelerate
# ALCF Vesta (BGQ)
BLAS = -L. -lMADMTXM -L/soft/libraries/essl/5.1.1-0/lib64/ -lesslbg -L/soft/libraries/alcf/current/xl/LAPACK/lib -llapack -lesslbg -L${IBM_MAIN_DIR}/xlsmp/bg/3.1/bglib64 -L${IBM_MAIN_DIR}/xlf/bg/14.1/bglib64/ -lxlsmp -lxlopt -lxlf90_r -lxlfmath -lxl -ldl -lrt
LIBS += -L/Users/jhammond/eclipse/MADNESS/CORAL/tbb41_20130314oss/build/macos_intel64_clang_cc4.2.1_os10.7.5_release -ltbb

# Jeff's Mac
#BLAS = -framework Accelerate
# ALCF Vesta (BGQ)
BLAS = -L. -lMADMTXM -L/soft/libraries/essl/5.1.1-0/lib64/ -lesslbg -L/soft/libraries/alcf/current/xl/LAPACK/lib -llapack -lesslbg -L${IBM_MAIN_DIR}/xlsmp/bg/3.1/bglib64 -L${IBM_MAIN_DIR}/xlf/bg/14.1/bglib64/ -lxlsmp -lxlopt -lxlf90_r -lxlfmath -lxl -ldl -lrt

all: axpy.x reduce.x test_mtxmq.x test_Zmtxmq.x

test_mtxmq.x: test_mtxmq.cc
	$(CXX) $(CXXFLAGS) $< $(BLAS) -o $@

test_Zmtxmq.x: test_Zmtxmq.cc
	$(CXX) $(INCLUDE) $< $(BLAS) -o $@

axpy.x: axpy.cc
	$(CXX) $(CXXFLAGS) $< $(LIBS) -o $@

reduce.x: reduce.cc
	$(CXX) $(CXXFLAGS) $< $(LIBS) -o $@

clean:
	-rm -f axpy.x reduce.x test_mtxmq.x test_Zmtxmq.x

