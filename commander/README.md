# TAU Commander

## Requirements

 * [Node.js >0.10.x](http://nodejs.org/)

## Quick Start

```
npm install
./bin/start.sh
```
Navigate to ```http://localhost:3000/``` and enjoy.

## Slow Start

You can install Node.js via your package manager but *be certain* that your 
distro comes with the right version. If not, go to http://nodejs.org and 
download/install direct from the source.

Once you have Node.js, install supervisor via npm:
```console
sudo npm install -g supervisor
```
Now follow the instructions under ***Quick Start***.

## Shell Scripts

 * ```dev_start.sh``` starts the taucmdr.js node app in single-CPU mode with
  hot-realoading of code enabled. Use for active development.
 * `start.sh` starts taucmdr.js without hot-reloading, but with as many child
  processes as you have CPU cores. Use for production.
 * stop.sh is a counterpart of start.sh to easily stop running background processes.

## Runtime Environment

These environment variables change runtime behavior and startup mode:

* ```NODE_ENV``` - defaults to "production"
* ```NODE_CLUSTERED``` - defaults to 1 (on)
* ```NODE_HOT_RELOAD``` - defaults to 0 (off)
* ```NODE_SERVE_STATIC``` - defaults to 0 (off) - Tip: don't use Node to serve static
  content in production
* ```NODE_CONFIG_DIR``` - defaults to "config" folder in the current folder
* ```NODE_LOG_DIR``` - defaults to "logs" folder in the current folder

## Hot Reloading vs. Daemon-izing Script.

In production environments it is a good idea to daemon-ize your Node process using Forever.js. Forever will restart
the process if it accidentally crashes.

In development, it is much more important to have "hot-reloading" of code available. This feature can be provided
with Supervisor.js package. If you set ```NODE_HOT_RELOAD``` to 1, start.sh will run in hot-reloading mode watching your
main script, libs folder and config folder.

Unfortunately, Supervisor and Forever packages do not work nicely with each other, so you can only use one
or the other, at this point. Setting ```NODE_HOT_RELOAD``` to 1 disables backgrounding of your script and runs your Node
application in foreground (which, to be fair, in most cases, is what you probably want during development, anyway).

## File Limits

Hot reloading uses native file watching features of \*nix systems. This is extremely handy and efficient, but 
unfortunately most systems have very low limits on watched and open files. If you use hot reloading a lot, you should
expect to see: "Error: watch EMFILE" or similar.

To solve the problem you need to raise your filesystem limits. This may be a two-step process. On Linux, there're hard
limits (something root user can change in /etc/limits.conf or /ets/security/limits.conf) that govern the limits individual
users can alter from command-line.

Put something like this (as root) in your /etc/limits.conf or /etc/security/limits.conf:

```bash
* hard nofile 10000
```

Then log out, log back in and run:

```bash
> ulimit -n 10000
```

You should probably put `ulimit -n 10000` in your .profile file, because it does not persist between restarts.

For OS-X and Solaris-specific instructions see [a Stackoverflow Answer](http://stackoverflow.com/questions/34588/how-do-i-change-the-number-of-open-files-limit-in-linux/34645#34645)

On certain Linux distributions you may also need to raise iNotify limit:

```bash
sysctl fs.inotify.max_user_instances=16384 && echo sysctl fs.inotify.max_user_instances=16384  | sudo tee /etc/rc.local  
```

And last, but not least, it's a good idea to also run:

```bash
> sudo sysctl -w kern.maxfiles=40960 kern.maxfilesperproc=20480
```

## Compatibility

We try to keep Node Bootstrap updated with the latest versions of Node, Express and Bootstrap. In some cases, where it
makes sense, branches compatible with older versions are created: <https://github.com/inadarei/nodebootstrap/branches> to
make upgrade path smoother.

## License

See LICENSE file.
