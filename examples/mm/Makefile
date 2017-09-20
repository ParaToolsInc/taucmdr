RM = /bin/rm -rf

TARGET = matmult.exe$(SUFFIX)

OBJS = matmult.o matmult_initialize.o

ifdef MPI
CC = tau mpicc
MPI_CFLAGS = -DTAU_MPI
SUFFIX=.mpi
else
CC = tau gcc
MPI_CFLAGS = 
SUFFIX=
endif

ifdef OPENMP
OMP_FLAGS = -fopenmp -DTAU_OPENMP
SUFFIX=.openmp
else
OMP_FLAGS = 
endif

CFLAGS = $(MPI_CFLAGS) $(OMP_FLAGS)
LDFLAGS = $(MPI_CFLAGS) $(OMP_FLAGS)

##############################################

.PHONY: all clean

all: $(TARGET)

$(TARGET): $(OBJS)
	$(CC) $(LDFLAGS) $(OBJS) -o $@ $(LIBS)

matmult.o: matmult.c
	$(CC) $(CFLAGS) -c $< -o $@

matmult_initialize.o: matmult_initialize.c matmult_initialize.h
	$(CC) $(CFLAGS) -c $< -o $@

clean:
	$(RM) $(OBJS) $(TARGET)*  profile.* *.trc *.edf *.z MULT* *.inst.* *.pdb Comp_gnu.o *.pomp.* *.opari.inc pompregions.* *.output *.error *.cobaltlog
