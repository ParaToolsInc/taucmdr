CC = gcc
CFLAGS = 
LDFLAGS =

RM = /bin/rm -rf

TARGET = matmult

OBJS = matmult.o matmult_initialize.o

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
	$(RM) $(OBJS) $(TARGET) profile.* *.trc *.edf *.z MULT* *.inst.* *.pdb Comp_gnu.o *.pomp.* *.opari.inc pompregions.* *.output *.error *.cobaltlog

