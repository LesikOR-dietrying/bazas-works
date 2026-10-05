export type OrderStatus = 'DRAFT' | 'CONFIRMED' | 'MATERIALS' | 'PRODUCTION' | 'READY' | 'PARTIALLY_SHIPPED' | 'SHIPPED' | 'CANCELLED'
export type VariantStatus = 'DRAFT' | 'PENDING_APPROVAL' | 'APPROVED' | 'REJECTED' | 'RELEASED'
export interface Customer { id: string; name: string; contact_details: string; notes: string }
export interface Order { id: string; order_number: string; customer_id: string; customer_name: string; recipient: string; destination: string; order_date: string; deadline: string | null; status: OrderStatus; notes: string; draft_version: number; total_quantity: number; product_summary: string; created_at: string; updated_at: string }
export interface RevisionOption { id: string; product_id: string; product_name: string; variant_id: string; variant_name: string; revision_code: string }
export interface OrderItem { id: string; order_id: string; product_id: string; product_revision_id: string; product_name: string; revision_code: string; quantity: number; required_date: string | null; notes: string }
export interface OrderVariant { id: string; order_item_id: string; name: string; quantity: number; is_standard: boolean; status: VariantStatus; notes: string }
export interface Deviation { id: string; variant_id: string; original_bom_item_id: string; replacement_component_id: string; quantity_per_product: string; reason: string; approved_at: string | null }
export interface Requirement { id: string; component_id: string; component_name: string; uom_id: string; required_quantity: string }
export interface MaterialSummary { component_id: string; component_name: string; uom_id: string; uom_code: string; required: string; received: string; ordered: string; in_transit: string; uncovered: string; launch_shortage: string }
export interface RequirementPreviewAlternative { component_id: string; component_name: string; component_sku: string | null; notes: string }
export interface RequirementPreviewRow { bom_item_id: string; position: string; component_id: string; component_name: string; component_sku: string | null; quantity_per_product: string; total_quantity: string; uom_id: string; uom_code: string; alternatives: RequirementPreviewAlternative[] }
export interface BomItem { id: string; component_id: string; quantity: string; position: string }
export interface ComponentOption { id: string; name: string; sku: string | null }
export interface Supplier { id: string; name: string }
export type ProcurementStatus = 'REQUIRED' | 'RFQ' | 'ORDERED' | 'PAID' | 'IN_TRANSIT' | 'CUSTOMS' | 'RECEIVED' | 'ISSUE'
export interface ProcurementRecord { id: string; component_id: string; component_name: string; uom_id: string; uom_code: string; supplier_id: string | null; supplier_name: string | null; quantity: string; status: ProcurementStatus; expected_date: string | null; tracking_number: string }
export interface ProcurementAllocation { id: string; procurement_record_id: string; requirement_id: string; quantity: string }
export type ExecutionStatus = 'WAITING' | 'READY' | 'IN_PROGRESS' | 'PASSED' | 'FAILED' | 'CANCELLED'
export interface ProductionItem { id: string; identifier: string; tracking_mode: string; quantity: number; variant_id: string; variant_name: string; product_name: string; revision_code: string; order_number: string; qr_value: string }
export interface StageExecution { id: string; production_item_id: string; stage_id: string; stage_code: string; stage_name: string; planned_quantity: number; completed_quantity: number; status: ExecutionStatus; assigned_user_id: string | null; started_at: string | null; completed_at: string | null; result_note: string }
export interface WorkItem { item: ProductionItem; execution: StageExecution }
export interface ChecklistTemplate { id: string; block_id: string; sequence: number; text: string; required: boolean; note_required: boolean; photo_required: boolean }
export interface ContentBlock { id: string; operation_id: string; block_type: 'TEXT' | 'IMAGE' | 'CHECKLIST' | 'WARNING' | 'FILE' | 'ANNOTATED_IMAGE' | 'MEASUREMENT' | 'VIDEO'; sequence: number; payload: Record<string, unknown>; attachment_id: string | null; annotation_source: Record<string, unknown>; annotation_version: number }
export interface FirmwareFile { purpose: string; artifact_name: string; release_version: string; description: string; config_text: string; binary_attachment_id: string | null; config_attachment_id: string | null }
export interface ExecutionDetail { item: ProductionItem; execution: StageExecution; instructions: string; operation_name: string | null; expected_result: string; acceptance_criteria: string; blocks: ContentBlock[]; checklist: ChecklistTemplate[]; firmware: FirmwareFile[] }
export interface StageProgress { stage_code: string; stage_name: string; completed: number; total: number }
export interface OrderProgress { order_id: string; completed: number; total: number; percent: number; stages: StageProgress[] }
export interface ProductionQueueOrder { order_id: string; order_number: string; customer_name: string; deadline: string | null; status: 'PRODUCTION' | 'READY'; completed_quantity: number; planned_quantity: number; percent: number; active_operations: number; blocked_operations: number; assignees: string[]; current_item_id: string | null; current_item_identifier: string | null; stages: StageProgress[] }
