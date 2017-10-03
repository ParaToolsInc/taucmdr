F90 = mpif90
FFLAGS = -O -g -fopenmp
LIBS= -fopenmp

SRC = matmult.f90
OBJ = $(SRC:.f90=.o)


matmult: $(OBJ)
	$(F90) $(FFLAGS) $(OBJ) -o matmult $(LIBS)

%.o: %.f90
	echo "Building $@ from $<"
	$(F90) $(FFLAGS) -c $< -o $@

clean:
	rm -f $(OBJ) matmult

