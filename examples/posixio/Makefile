RM = /bin/rm -rf

CC = gcc

TARGET = posixio

OBJS = posixio.o

CFLAGS = 
LDFLAGS = 

##############################################

.PHONY: all clean

all: $(TARGET)

$(TARGET): $(OBJS)
	$(CC) $(LDFLAGS) $(OBJS) -o $@ $(LIBS)

%.o: %.c
	$(CC) $(CFLAGS) -c $< -o $@

clean:
	$(RM) $(OBJS) $(TARGET) out.dat profile.* *.trc *.edf *.z MULT* *.inst.* *.pdb Comp_gnu.o *.pomp.* *.opari.inc pompregions.* *.output *.error *.cobaltlog
