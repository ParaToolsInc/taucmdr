from notebook.utils import url_path_join
from notebook.base.handlers import IPythonHandler
from tornado import web

import os
import json

from taucmdr import util
from taucmdr.cf.compiler.host import CC
from taucmdr.cf.compiler.mpi import MPI_CC
from taucmdr.cf.compiler.shmem import SHMEM_CC
from taucmdr.cf.storage.levels import PROJECT_STORAGE
from taucmdr.model.project import Project


class ProjectDetailsHandler(web.RequestHandler):
    def get(self):
        def yn(v):
            return "yes" if v else "no"

        ds = {
                "targets": [],
                "applications": [],
                "measurements": [],
                "experiments": []
        }

        pname = self.get_argument("project")
        p = Project.controller().one({'name': pname})

        # targets
        rs = p.populate("targets")
        for r in rs:
            r = r.populate()
            mpicc = MPI_CC.keyword
            shmcc = SHMEM_CC.keyword
            d = {
                    "name": r["name"],
                    "host_os": r["host_os"],
                    "host_arch": r["host_arch"],
                    "host_compilers": r[CC.keyword]["family"],
                    "mpi_compilers": r[mpicc]["family"] if mpicc in r else "None",
                    "shmem_compilers": r[shmcc]["family"] if shmcc in r else "None"
            }
            ds["targets"].append(d)

        # applications
        rs = p.populate("applications")
        for r in rs:
            r = r.populate() 
            d = {
                    "name": r["name"],
                    "linkage": r["linkage"],
                    "openmp": yn(r["openmp"]),
                    "pthreads": yn(r["pthreads"]),
                    "tbb": yn(r["tbb"]),
                    "mpi": yn(r["mpi"]),
                    "cuda": yn(r["cuda"]),
                    "opencl": yn(r["opencl"]),
                    "shmem": yn(r["shmem"]),
                    "mpc": yn(r["mpc"])
            }
            ds["applications"].append(d)

        # measurements
        rs = p.populate("measurements")
        for r in rs:
            r = r.populate()
            d = {
                    "name": r["name"],
                    "profile": r["profile"],
                    "trace": r["trace"],
                    "sample": yn(r["sample"]),
                    "source_inst": r["source_inst"],
                    "compiler_inst": r["compiler_inst"],
                    "openmp": r["openmp"],
                    "cuda": yn(r["cuda"]),
                    "io": yn(r["io"]),
                    "mpi": yn(r["mpi"]),
                    "shmem": yn(r["shmem"])
            }
            ds["measurements"].append(d)

        # experiments
        rs = p.populate("experiments")
        for r in rs:
            r = r.populate()
            d = {
                    "name": r["name"],
                    "num_trials": str(len(r["trials"])),
                    "data_size": util.human_size(sum(int(t.get('data_size', 0)) for t in r["trials"])),
                    "target": r["target"]["name"],
                    "application": r["application"]["name"],
                    "measurement": r["measurement"]["name"],
                    "tau_makefile": r["tau_makefile"]
            }
            ds["experiments"].append(d)

        self.set_header("Access-Control-Allow-Origin", "*")
        self.finish(ds)

class ListProjectsHandler(web.RequestHandler):
    def get(self):
        ds = []
        ns = [p['name'] for p in Project.controller().all()]

        for n in ns:
            p = Project.controller().one({'name': n})

            d = {
                    "name": n,
                    "targets": [x['name'] for x in p.populate('targets')],
                    "applications": [x['name'] for x in p.populate('applications')],
                    "measurements": list(set([x['name'] for x in p.populate('measurements')])),
                    "num_experiments": len(p['experiments'])
            }
            ds.append(d)

        self.set_header("Access-Control-Allow-Origin", "*")
        self.finish({
            "projects": ds
        })

def load_jupyter_server_extension(nb_server_app):
    wa = nb_server_app.web_app
    host_pattern = '.*$'
    list_projects_route = url_path_join(wa.settings['base_url'], '/list_projects')
    project_details_route = url_path_join(wa.settings['base_url'], '/project_details')
    wa.add_handlers(host_pattern, [ 
        (list_projects_route, ListProjectsHandler),
        (project_details_route, ProjectDetailsHandler)
    ])
