F90 = mpiifort
FFLAGS = -O -g -traceback
LIBS= -qopenmp

SRC = $(wildcard *.f90)
OBJ = $(SRC:.f90=.o)


matmult: $(OBJ)
	$(F90) $(FFLAGS) $(OBJ) -o matmult $(LIBS)

%.o: %.f90
	echo "Building $@ from $<"
	$(F90) $(FFLAGS) -c $< -o $@

clean:
	rm -f $(OBJ) matmult

