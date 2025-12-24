-- Create uploads bucket for PDF storage
-- Public bucket for MVP

INSERT INTO storage.buckets (id, name, public)
VALUES ('uploads', 'uploads', true)
ON CONFLICT (id) DO NOTHING;

-- Policy for INSERT (required for uploads)
CREATE POLICY "Allow uploads to bucket"
ON storage.objects FOR INSERT
WITH CHECK (bucket_id = 'uploads');

-- Policy for SELECT (required for downloads)
CREATE POLICY "Allow reads from bucket"
ON storage.objects FOR SELECT
USING (bucket_id = 'uploads');

-- Policy for DELETE (required for file deletion)
CREATE POLICY "Allow deletes from bucket"
ON storage.objects FOR DELETE
USING (bucket_id = 'uploads');
