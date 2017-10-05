CC = tau mpicc
CFLAGS = -O -g -fopenmp

LD = $(CC)
LDFLAGS = $(CFLAGS)
LIBS= 

COMMON_SRC = logging.c

MASTER_SRC = master.c $(COMMON_SRC)
MASTER_OBJ = $(MASTER_SRC:.c=.o)
MASTER_EXE = master

WORKER1_SRC = worker1.c $(COMMON_SRC)
WORKER1_OBJ = $(WORKER1_SRC:.c=.o)
WORKER1_EXE = worker1

WORKER2_SRC = worker2.c $(COMMON_SRC)
WORKER2_OBJ = $(WORKER2_SRC:.c=.o)
WORKER2_EXE = worker2

WORKER3_SRC = worker3.c $(COMMON_SRC)
WORKER3_OBJ = $(WORKER3_SRC:.c=.o)
WORKER3_EXE = worker3

WORKER_SRC = worker1.c worker2.c worker3.c
OBJ = $(MASTER_OBJ) $(WORKER1_OBJ) $(WORKER2_OBJ) $(WORKER3_OBJ)
EXES = $(MASTER_EXE) $(WORKER1_EXE) $(WORKER2_EXE) $(WORKER3_EXE)

.PHONY: all run clean
.DEFAULT: all

all: $(EXES)

run: all
	tau mpirun -np 1 ./master : -np 1 ./worker1 : -np 2 ./worker2 : -np 3 ./worker3

$(MASTER_EXE): $(MASTER_OBJ)
	$(LD) -o $@ $(LDFLAGS) $^ $(LIBS)

$(WORKER1_EXE): $(WORKER1_OBJ)
	$(LD) -o $@ $(LDFLAGS) $^ $(LIBS)

$(WORKER2_EXE): $(WORKER2_OBJ)
	$(LD) -o $@ $(LDFLAGS) $^ $(LIBS)

$(WORKER3_EXE): $(WORKER3_OBJ)
	$(LD) -o $@ $(LDFLAGS) $^ $(LIBS)

worker%.c: worker.c
	ln -s worker.c $@

%.o: %.c
	$(CC) $(CFLAGS) -c $< -o $@

clean:
	rm -f $(OBJ) $(EXES) $(WORKER_SRC)

