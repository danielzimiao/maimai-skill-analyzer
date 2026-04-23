export interface AnalysisResult {
  difficulty: number | null
  tags: string[]
  similar_songs: Array<{
    name: string
    difficulty: number | null
    release_date: string | null
    bg_image_url: string | null
  }>
}

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export async function analyzeChart(file: File): Promise<AnalysisResult> {
  const formData = new FormData()
  formData.append('file', file)

  const response = await fetch(`${API_URL}/analyze`, {
    method: 'POST',
    body: formData,
  })

  if (!response.ok) {
    const err = await response.json().catch(() => ({}))
    throw new Error(err.error || err.detail || `Server error: ${response.status}`)
  }

  return response.json()
}

export async function getTags(
  tag: string,
): Promise<{ tag: string; songs: AnalysisResult['similar_songs'] }> {
  const response = await fetch(`${API_URL}/tags/${encodeURIComponent(tag)}`)
  if (!response.ok) throw new Error(`Server error: ${response.status}`)
  return response.json()
}
