export type FileOwner = { kind: 'project' | 'branch' | 'task' | 'setup' | 'component' | 'test' | 'firmware_revision' | 'product' | 'product_revision' | 'firmware_release'; id: string }
export type CommentOwner = { kind: 'project' | 'branch' | 'task' | 'setup' | 'test'; id: string }
export function ownerField(owner: FileOwner | CommentOwner): string { return `${owner.kind}_id` }

export interface Attachment {
  id: string; original_filename: string; mime_type: string; size: number; uploaded_by_id: string
  uploaded_by_name: string; created_at: string
  project_id: string | null; branch_id: string | null; task_id: string | null; setup_id: string | null
  component_id: string | null; test_id: string | null; firmware_revision_id: string | null
  product_id: string | null; product_revision_id: string | null; firmware_release_id: string | null
}

export interface Comment {
  id: string; author_id: string; author_name: string; text: string; created_at: string; updated_at: string
  project_id: string | null; branch_id: string | null; task_id: string | null; setup_id: string | null; test_id: string | null
}
