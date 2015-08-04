F90 = mpif90
RM = /bin/rm -rf

TARGET = matmult

OBJS = matmult.o
CFLAGS=-g
LDFLAGS=-g

##############################################

.PHONY: all clean
.SUFFIXES : .f90

all: $(TARGET)

$(TARGET): $(OBJS)
	$(F90) $(LDFLAGS) $(OBJS) -o $@ $(LIBS)

matmult.o: matmult.f90
	$(F90) $(CFLAGS) -c $< -o $@

clean:
	$(RM) $(OBJS) $(TARGET) profile.* *.trc *.edf *.z MULT* *.inst.* *.pdb Comp_gnu.o *.pomp.* *.opari.inc pompregions.* *.output *.error *.cobaltlog
