interface Property {
  [prop: string]: string | number | boolean
}

interface Field {
  [field: string]: Property
}

interface Project {
  [name: string]: Field
}

export interface ProjectList {
  [projects: string]: Project
}

