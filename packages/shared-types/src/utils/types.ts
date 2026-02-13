// Utility types

export type UUID = string

export type Timestamp = Date | string

export type Nullable<T> = T | null

export type Optional<T> = T | undefined

export type DeepPartial<T> = {
  [P in keyof T]?: T[P] extends object ? DeepPartial<T[P]> : T[P]
}

export type RequiredFields<T, K extends keyof T> = T & Required<Pick<T, K>>

export type OmitStrict<T, K extends keyof T> = Pick<T, Exclude<keyof T, K>>
