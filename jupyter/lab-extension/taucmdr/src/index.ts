import {
  JupyterFrontEnd,
  JupyterFrontEndPlugin
} from '@jupyterlab/application';

import {
  ICommandPalette,
  MainAreaWidget
} from '@jupyterlab/apputils';

import {
  Widget
} from '@lumino/widgets';

interface Project {
  name: string;
  targets: Array<string>;
  applications: Array<string>;
  measurements: Array<string>;
  num_experiments: string;
}

interface ProjectList {
  projects: Array<Project>;
}

interface Target {
  name: string;
  host_os: string;
  host_arch: string;
  host_compilers: string;
  mpi_compilers: string;
  shmem_compilers: string;
}

interface Application {
  name: string;
  linkage: string;
  openmp: string;
  pthreads: string;
  tbb: string;
  mpi: string;
  cuda: string;
  opencl: string;
  shmem: string;
  mpc: string;
}

interface Measurement {
  name: string;
  profile: string;
  trace: string;
  sample: string;
  source_inst: string;
  compiler_inst: string;
  openmp: string;
  cuda: string;
  io: string;
  mpi: string;
  shmem: string;
}

interface Experiment {
  name: string;
  num_trials: string;
  data_size: string;
  target: string;
  application: string;
  measurement: string;
  tau_makefile: string;
}

interface ProjectDetails {
  targets: Array<Target>;
  applications: Array<Application>;
  measurements: Array<Measurement>;
  experiments: Array<Experiment>;
}

const taucmdr_api_host = "192.168.1.54"
const taucmdr_api_port = "8888"
const taucmdr_api_ep = "http://" + taucmdr_api_host + ":" + taucmdr_api_port;
const list_projects_ep = taucmdr_api_ep + "/list_projects";
const project_details_ep = taucmdr_api_ep + "/project_details";

async function fetchWithTimeout (uri : string, options = {}, time = 5000) {
  const controller = new AbortController();
  const config = { ...options, signal: controller.signal }

  const timeout = setTimeout(() => {
    controller.abort()
  }, time);

  return fetch(uri, config)
    .then((res) => {
      if (!res.ok) {
        throw new Error(`${res.status}: ${res.statusText}`);
      }
      return res;
    })
    .catch((err) => {
      if (err.name == 'AbortError') {
        throw new Error("Response timed out");
      }
      throw new Error(err.message);
    });
}

async function fetch_project_list() : Promise<ProjectList> {
  const url = list_projects_ep;
  return fetchWithTimeout(url, {}, 1000).then(async (res) => {
      return await res.json();
  });
}

function fetch_project_list_fake() : Promise<ProjectList> {
  const res = `{
    "projects": [
      {
        "applications": [
          "taucmdr-jup"
        ],
        "measurements": [
          "profile",
          "baseline",
          "trace",
          "sample",
          "source-inst",
          "compiler-inst"
        ],
        "name": "taucmdr-jup",
        "num_experiments": 1,
        "targets": [
          "bigwalker"
        ]
      }
    ]
  }`;
  return new Promise((resolve, _) => {
    resolve(JSON.parse(res) as ProjectList);
  });
}

async function fetch_project_details(name : string) : Promise<ProjectDetails> {
  const url = project_details_ep + "?project=" + encodeURIComponent(name);
  return fetchWithTimeout(url, {}, 1000).then(async (res) => {
    return await res.json();
  });
}

function fetch_project_details_fake(name : string) : Promise<ProjectDetails> {
  const res = `{
    "experiments": [
      {
        "target": "bigwalker",
        "application": "taucmdr-jup",
        "num_trials": "0",
        "measurement": "sample",
        "tau_makefile": "Makefile.tau-50a0d0b3",
        "data_size": "0.0B",
        "name": "bigwalker-taucmdr-jup-sample"
      }
    ],
    "applications": [
      {
        "opencl": "no",
        "cuda": "no",
        "tbb": "no",
        "mpc": "no",
        "name": "taucmdr-jup",
        "openmp": "no",
        "pthreads": "no",
        "shmem": "no",
        "linkage": "dynamic",
        "mpi": "no"
      }
    ],
    "measurements": [
      {
        "profile": "tau",
        "trace": "none",
        "mpi": "no",
        "sample": "no",
        "io": "no",
        "openmp": "ignore",
        "compiler_inst": "never",
        "name": "baseline",
        "cuda": "no",
        "source_inst": "never",
        "shmem": "no"
      },
      {
        "profile": "tau",
        "trace": "none",
        "mpi": "no",
        "sample": "yes",
        "io": "no",
        "openmp": "ignore",
        "compiler_inst": "never",
        "name": "sample",
        "cuda": "no",
        "source_inst": "never",
        "shmem": "no"
      },
      {
        "profile": "tau",
        "trace": "none",
        "mpi": "no",
        "sample": "no",
        "io": "no",
        "openmp": "ignore",
        "compiler_inst": "fallback",
        "name": "profile",
        "cuda": "no",
        "source_inst": "automatic",
        "shmem": "no"
      },
      {
        "profile": "tau",
        "trace": "none",
        "mpi": "no",
        "sample": "no",
        "io": "no",
        "openmp": "ignore",
        "compiler_inst": "never",
        "name": "source-inst",
        "cuda": "no",
        "source_inst": "automatic",
        "shmem": "no"
      },
      {
        "profile": "tau",
        "trace": "none",
        "mpi": "no",
        "sample": "no",
        "io": "no",
        "openmp": "ignore",
        "compiler_inst": "always",
        "name": "compiler-inst",
        "cuda": "no",
        "source_inst": "never",
        "shmem": "no"
      },
      {
        "profile": "none",
        "trace": "otf2",
        "mpi": "no",
        "sample": "no",
        "io": "no",
        "openmp": "ignore",
        "compiler_inst": "fallback",
        "name": "trace",
        "cuda": "no",
        "source_inst": "automatic",
        "shmem": "no"
      }
    ],
    "targets": [
      {
        "shmem_compilers": "None",
        "name": "bigwalker",
        "host_compilers": "GNU",
        "host_arch": "x86_64",
        "host_os": "Linux",
        "mpi_compilers": "None"
      }
    ]
  }`;
  return new Promise((resolve, _) => {
    resolve(JSON.parse(res) as ProjectDetails);
  });
}

let projects_tbl : HTMLTableElement;
let projects_tbl_head : HTMLTableSectionElement;
let projects_tbl_headrow : HTMLTableRowElement;
let projects_tbl_body : HTMLTableSectionElement;
const projects_tbl_fields = [
  "Name",
  "Targets",
  "Applications",
  "Measurements",
  "# Experiments"
];

let targets_tbl : HTMLTableElement;
let targets_tbl_head : HTMLTableSectionElement;
let targets_tbl_headrow : HTMLTableRowElement;
let targets_tbl_body : HTMLTableSectionElement;
const targets_tbl_fields = [
  "Name",
  "Host OS",
  "Host Arch",
  "Host Compilers",
  "MPI Compilers",
  "SHMEM Compilers"
];

let applications_tbl : HTMLTableElement;
let applications_tbl_head : HTMLTableSectionElement;
let applications_tbl_headrow : HTMLTableRowElement;
let applications_tbl_body : HTMLTableSectionElement;
const applications_tbl_fields = [
  "Name",
  "Linkage",
  "OpenMP",
  "Pthreads",
  "TBB",
  "MPI",
  "CUDA",
  "OpenCL",
  "SHMEM",
  "MPC"
];

let measurements_tbl : HTMLTableElement;
let measurements_tbl_head : HTMLTableSectionElement;
let measurements_tbl_headrow : HTMLTableRowElement;
let measurements_tbl_body : HTMLTableSectionElement;
const measurements_tbl_fields = [
  "Name",
  "Profile",
  "Trace",
  "Sample",
  "Source Inst.",
  "Compiler Inst.",
  "OpenMP",
  "CUDA",
  "I/O",
  "MPI",
  "SHMEM"
];

let experiments_tbl : HTMLTableElement;
let experiments_tbl_head : HTMLTableSectionElement;
let experiments_tbl_headrow : HTMLTableRowElement;
let experiments_tbl_body : HTMLTableSectionElement;
const experiments_tbl_fields = [
  "Name",
  "# Trials",
  "Data Size",
  "Target",
  "Application",
  "Measurement",
  "TAU Makefile"
];

function projects_tbl_init() {
  projects_tbl = document.createElement("table");
  projects_tbl.setAttribute("id", "projects-tbl");
  projects_tbl_head = projects_tbl.createTHead();
  let r = projects_tbl_head.insertRow();
  let c = document.createElement("th");
  c.setAttribute("colspan", projects_tbl_fields.length.toString());
  c.setAttribute("class", "tbl-title");
  c.appendChild(document.createTextNode("Projects"));
  r.appendChild(c);

  projects_tbl_headrow = projects_tbl_head.insertRow();
  projects_tbl_body = projects_tbl.createTBody();

  projects_tbl_fields.forEach( f => {
    let c = document.createElement("th");
    c.appendChild(document.createTextNode(f));
    projects_tbl_headrow.appendChild(c);
  });
}

function targets_tbl_init() {
  targets_tbl = document.createElement("table");
  targets_tbl.setAttribute("id", "targets-tbl");
  targets_tbl_head = targets_tbl.createTHead();
  let r = targets_tbl_head.insertRow();
  let c = document.createElement("th");
  c.setAttribute("colspan", targets_tbl_fields.length.toString());
  c.setAttribute("class", "tbl-title");
  c.appendChild(document.createTextNode("Targets"));
  r.appendChild(c);

  targets_tbl_headrow = targets_tbl_head.insertRow();
  targets_tbl_body = targets_tbl.createTBody();

  targets_tbl_fields.forEach( f => {
    let c = document.createElement("th");
    c.appendChild(document.createTextNode(f));
    targets_tbl_headrow.appendChild(c);
  });
}

function applications_tbl_init() {
  applications_tbl = document.createElement("table");
  applications_tbl.setAttribute("id", "applications-tbl");
  applications_tbl_head = applications_tbl.createTHead();
  let r = applications_tbl_head.insertRow();
  let c = document.createElement("th");
  c.setAttribute("colspan", applications_tbl_fields.length.toString());
  c.setAttribute("class", "tbl-title");
  c.appendChild(document.createTextNode("Applications"));
  r.appendChild(c);

  applications_tbl_headrow = applications_tbl_head.insertRow();
  applications_tbl_body = applications_tbl.createTBody();

  applications_tbl_fields.forEach( f => {
    let c = document.createElement("th");
    c.appendChild(document.createTextNode(f));
    applications_tbl_headrow.appendChild(c);
  });
}

function measurements_tbl_init() {
  measurements_tbl = document.createElement("table");
  measurements_tbl.setAttribute("id", "measurements-tbl");
  measurements_tbl_head = measurements_tbl.createTHead();
  let r = measurements_tbl_head.insertRow();
  let c = document.createElement("th");
  c.setAttribute("colspan", measurements_tbl_fields.length.toString());
  c.setAttribute("class", "tbl-title");
  c.appendChild(document.createTextNode("Measurements"));
  r.appendChild(c);

  measurements_tbl_headrow = measurements_tbl_head.insertRow();
  measurements_tbl_body = measurements_tbl.createTBody();
  
  measurements_tbl_fields.forEach( f => {
    let c = document.createElement("th");
    c.appendChild(document.createTextNode(f));
    measurements_tbl_headrow.appendChild(c);
  });
}

function experiments_tbl_init() {
  experiments_tbl = document.createElement("table");
  experiments_tbl.setAttribute("id", "experiments-tbl");
  experiments_tbl_head = experiments_tbl.createTHead();
  let r = experiments_tbl_head.insertRow();
  let c = document.createElement("th");
  c.setAttribute("colspan", experiments_tbl_fields.length.toString());
  c.setAttribute("class", "tbl-title");
  c.appendChild(document.createTextNode("Experiments"));
  r.appendChild(c);

  experiments_tbl_headrow = experiments_tbl_head.insertRow();
  experiments_tbl_body = experiments_tbl.createTBody();

  experiments_tbl_fields.forEach( f => {
    let c = document.createElement("th");
    c.appendChild(document.createTextNode(f));
    experiments_tbl_headrow.appendChild(c);
  });
}

function update_projects_tbl(ds: ProjectList) {
  projects_tbl_body.innerHTML = "";

  ds.projects.forEach( (p : Project) => {
    let r = projects_tbl_body.insertRow();
  
    let c = r.insertCell();
    c.appendChild(document.createTextNode(p.name));

    c = r.insertCell();
    c.appendChild(document.createTextNode(p.targets.join(", ")));

    c = r.insertCell();
    c.appendChild(document.createTextNode(p.applications.join(", ")));

    c = r.insertCell();
    c.appendChild(document.createTextNode(p.measurements.join(", ")));

    c = r.insertCell();
    c.appendChild(document.createTextNode(p.num_experiments.toString()));
    
    r.addEventListener("click", (el) => {
      display_project_details(p["name"]);
    });
  })
}

function update_targets_tbl(targets: Array<Target>) {
  targets_tbl_body.innerHTML = "";
  targets.forEach( t => {
    let r = targets_tbl_body.insertRow();

    let c = r.insertCell();
    c.appendChild(document.createTextNode(t.name));

    c = r.insertCell();
    c.appendChild(document.createTextNode(t.host_os));

    c = r.insertCell();
    c.appendChild(document.createTextNode(t.host_arch));

    c = r.insertCell();
    c.appendChild(document.createTextNode(t.host_compilers));

    c = r.insertCell();
    c.appendChild(document.createTextNode(t.mpi_compilers));

    c = r.insertCell();
    c.appendChild(document.createTextNode(t.shmem_compilers));
  });
}

function update_applications_tbl(applications: Array<Application>) {
  applications_tbl_body.innerHTML = "";
  applications.forEach( a => {
    let r = applications_tbl_body.insertRow();
    
    let c = r.insertCell();
    c.appendChild(document.createTextNode(a.name));

    c = r.insertCell();
    c.appendChild(document.createTextNode(a.linkage));

    c = r.insertCell();
    c.appendChild(document.createTextNode(a.openmp));

    c = r.insertCell();
    c.appendChild(document.createTextNode(a.pthreads));

    c = r.insertCell();
    c.appendChild(document.createTextNode(a.tbb));

    c = r.insertCell();
    c.appendChild(document.createTextNode(a.mpi));

    c = r.insertCell();
    c.appendChild(document.createTextNode(a.cuda));

    c = r.insertCell();
    c.appendChild(document.createTextNode(a.opencl));

    c = r.insertCell();
    c.appendChild(document.createTextNode(a.shmem));

    c = r.insertCell();
    c.appendChild(document.createTextNode(a.mpc));
  });
}

function update_measurements_tbl(measurements: Array<Measurement>) {
  measurements_tbl_body.innerHTML = "";
  measurements.forEach( m => {
    let r = measurements_tbl_body.insertRow();

    let c = r.insertCell();
    c.appendChild(document.createTextNode(m.name));

    c = r.insertCell();
    c.appendChild(document.createTextNode(m.profile));

    c = r.insertCell();
    c.appendChild(document.createTextNode(m.trace));

    c = r.insertCell();
    c.appendChild(document.createTextNode(m.sample));

    c = r.insertCell();
    c.appendChild(document.createTextNode(m.source_inst));

    c = r.insertCell();
    c.appendChild(document.createTextNode(m.compiler_inst));

    c = r.insertCell();
    c.appendChild(document.createTextNode(m.openmp));

    c = r.insertCell();
    c.appendChild(document.createTextNode(m.cuda));

    c = r.insertCell();
    c.appendChild(document.createTextNode(m.io));

    c = r.insertCell();
    c.appendChild(document.createTextNode(m.mpi));

    c = r.insertCell();
    c.appendChild(document.createTextNode(m.shmem));
  });
}

function update_experiments_tbl(experiments: Array<Experiment>) {
  experiments_tbl_body.innerHTML = "";
  experiments.forEach( e => {
    let r = experiments_tbl_body.insertRow();

    let c = r.insertCell();
    c.appendChild(document.createTextNode(e.name));

    c = r.insertCell();
    c.appendChild(document.createTextNode(e.num_trials));

    c = r.insertCell();
    c.appendChild(document.createTextNode(e.data_size));

    c = r.insertCell();
    c.appendChild(document.createTextNode(e.target));

    c = r.insertCell();
    c.appendChild(document.createTextNode(e.application));

    c = r.insertCell();
    c.appendChild(document.createTextNode(e.measurement));

    c = r.insertCell();
    c.appendChild(document.createTextNode(e.tau_makefile));
  });
}

function display_project_details(p: string) {
  fetch_project_details_fake(p).then( d => {
    update_targets_tbl(d.targets);
    update_applications_tbl(d.applications);
    update_measurements_tbl(d.measurements);
    update_experiments_tbl(d.experiments);
  }).catch( err => {
    console.log("error: display_project_details: ", err.message);
  });
}

function refresh_project_list() {
  fetch_project_list_fake().then( ds => {
    update_projects_tbl(ds);
  }).catch( err => {
    console.log("error: refresh_project_list: ", err.message);
  });
}

const extension: JupyterFrontEndPlugin<void> = {
  id: 'taucmdr',
  autoStart: true,
  requires: [ICommandPalette],
  activate: async (app: JupyterFrontEnd, palette: ICommandPalette) => {
    
    const content = new Widget();

    const widget = new MainAreaWidget({content});
    widget.id = 'tau_commander';
    widget.title.label = 'TAU Commander';
    widget.title.closable = true;

    let main = document.createElement("div");
    main.setAttribute("id", "main-wrapper");
    content.node.appendChild(main);

    // REFRESH PROJECTS BUTTON
    let refresh_projects_btn = document.createElement("button");
    refresh_projects_btn.innerHTML = "Refresh Project List"
    main.appendChild(refresh_projects_btn);

    // INSTRUCTIONS
    let instr = document.createElement("p");
    instr.setAttribute("id", "instructions");
    instr.innerHTML = "Click on one of the projects listed below to get more information.";
    main.appendChild(instr);

    // PROJECTS TABLE
    projects_tbl_init()
    main.appendChild(projects_tbl);

    // TARGETS TABLE
    targets_tbl_init();
    main.appendChild(targets_tbl);

    // APPLICATIONS TABLE
    applications_tbl_init();
    main.appendChild(applications_tbl);

    // MEASUREMENTS TABLE
    measurements_tbl_init();
    main.appendChild(measurements_tbl);

    // EXPERIMENTS TABLE
    experiments_tbl_init();
    main.appendChild(experiments_tbl);

    refresh_projects_btn.addEventListener("click", refresh_project_list);
    refresh_project_list();

    const command : string = 'taucmdr:open';
    app.commands.addCommand(command, {
      label: "TAU Commander",
      execute: () => {
        if (!widget.isAttached) {
          app.shell.add(widget, 'main');
        }
        app.shell.activateById(widget.id);
      }
    });

    palette.addItem({command, category: 'TAU'});
  }
};

export default extension;