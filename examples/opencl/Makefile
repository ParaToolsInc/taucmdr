OPENCL_PREFIX=/usr/local/cuda
OPENCL_LIB=-L$(OPENCL_PREFIX)/lib -lOpenCL
OPENCL_INC=-I$(OPENCL_PREFIX)/include

CXX=g++

all: matmult

matmult: matmult.o
	$(CXX) $(OPENCL_LIB) -g -o $@ $<

matmult.o: matmult.cpp
	$(CXX) -I$(OPENCL_INC) -g -c $< -o $@

clean:
	rm -rf matmult matmult.o
