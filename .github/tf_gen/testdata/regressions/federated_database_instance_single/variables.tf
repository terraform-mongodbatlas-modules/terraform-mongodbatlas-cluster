variable "mongodbatlas_federated_database_instance" {
  type = object({
    name       = string,
    project_id = string,
    cloud_provider_config = optional(object({
      aws = optional(object({
        role_id        = string,
        test_s3_bucket = string
      })),
      azure = optional(object({
        role_id = string
      }))
    })),
    data_process_region = optional(object({
      cloud_provider = string,
      region         = string
    })),
    storage_databases = optional(set(object({
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
    }))),
    storage_stores = optional(set(object({
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
    })))
  })
}