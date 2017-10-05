F90 = tau mpif90
FFLAGS = -O -g -fopenmp
LIBS= -fopenmp

SRC = matmult.f90
OBJ = $(SRC:.f90=.o)

.PHONY: all clean run
.DEFAULT: all

all: matmult

run: all
	export OMP_NUM_THREADS=4 ; \
	export MV2_ENABLE_AFFINITY=0 ; \
	tau mpirun -np 4 ./matmult

matmult: $(OBJ)
	$(F90) $(FFLAGS) $(OBJ) -o matmult $(LIBS)

%.o: %.f90
	echo "Building $@ from $<"
	$(F90) $(FFLAGS) -c $< -o $@

clean:
	rm -f $(OBJ) matmult

