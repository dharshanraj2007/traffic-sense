export interface StatusLog {
  id: number;
  violation_id: number;
  old_status: string;
  new_status: string;
  notes?: string;
  changed_at: string;
}

export interface Violation {
  id: number;
  fine_ref: string;
  plate_number: string;
  violation_type: string;
  location: string;
  occurred_at: string;
  fine_amount: number;
  status: 'Pending' | 'Paid' | 'Cancelled' | string;
  source: 'Manual' | 'AI' | string;
  confidence?: number;
  needs_review: boolean;
  evidence_url?: string;
  plate_crop_url?: string;
  video_job_id?: number;
  notes?: string;
  paid_at?: string;
  payment_ref?: string;
  created_at: string;
  updated_at: string;
  status_logs?: StatusLog[];
}

export interface ViolationListResponse {
  items: Violation[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface FineRule {
  id: number;
  violation_type: string;
  amount: number;
  active: boolean;
}

export interface DailyStat {
  date: string;
  count: number;
}

export interface StatusStat {
  name: string;
  value: number;
}

export interface DashboardStats {
  total_violations: number;
  pending_fines: number;
  paid_fines: number;
  cancelled_fines: number;
  total_collected_amount: number;
  total_pending_amount: number;
  needs_review_count: number;
  daily_stats: DailyStat[];
  status_distribution: StatusStat[];
  recent_violations: Violation[];
}

export interface VideoJob {
  id: number;
  filename: string;
  status: 'queued' | 'processing' | 'completed' | 'failed';
  progress: number;
  total_frames: number;
  vehicles_detected: number;
  violations_found: number;
  error?: string;
  created_at: string;
  finished_at?: string;
  violation_ids: number[];
}

export interface Admin {
  id: number;
  email: string;
  created_at: string;
}

export interface PublicFineResult {
  plate_number: string;
  total_violations: number;
  pending_violations: number;
  total_pending_amount: number;
  violations: Violation[];
}
