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

export async function analyzeChart(file: File): Promise<AnalysisResult> {
  // implemented in step 8
  void file
  throw new Error('Not implemented yet')
}

export async function getTags(
  tag: string,
): Promise<{ tag: string; songs: AnalysisResult['similar_songs'] }> {
  // implemented in step 10
  void tag
  throw new Error('Not implemented yet')
}
