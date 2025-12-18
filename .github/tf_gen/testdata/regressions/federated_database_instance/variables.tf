variable "name" {
  type = string
}

variable "project_id" {
  type = string
}

variable "cloud_provider_config" {
  type = object({
    aws = optional(object({
      role_id        = string,
      test_s3_bucket = string
    })),
    azure = optional(object({
      role_id = string
    }))
  })
  nullable = true
  default  = null
}

variable "data_process_region" {
  type = object({
    cloud_provider = string,
    region         = string
  })
  nullable = true
  default  = null
}

variable "storage_databases" {
  type = set(object({
    name = optional(string),
    collections = optional(set(object({
      name = optional(string),
      data_sources = optional(set(object({
        allow_insecure        = optional(bool),
        collection            = optional(string),
        collection_regex      = optional(string),
        database              = optional(string),
        database_regex        = optional(string),
        dataset_name          = optional(string),
        default_format        = optional(string),
        path                  = optional(string),
        provenance_field_name = optional(string),
        store_name            = optional(string),
        urls                  = optional(list(string))
      })))
    }))),
    views = optional(set(object({})))
  }))
  nullable = true
  default  = null
}

variable "storage_stores" {
  type = set(object({
    additional_storage_classes = optional(list(string)),
    allow_insecure             = optional(bool),
    bucket                     = optional(string),
    cluster_name               = optional(string),
    default_format             = optional(string),
    delimiter                  = optional(string),
    include_tags               = optional(bool),
    name                       = optional(string),
    prefix                     = optional(string),
    project_id                 = optional(string),
    provider                   = optional(string),
    public                     = optional(string),
    region                     = optional(string),
    urls                       = optional(list(string)),
    read_preference = optional(object({
      max_staleness_seconds = optional(number),
      mode                  = optional(string),
      tag_sets = optional(list(object({
        tags = list(object({
          name  = optional(string),
          value = optional(string)
        }))
      })))
    }))
  }))
  nullable = true
  default  = null
}