import { LoadErrorScreen } from '@/components/common/load-error-screen'
import { Visualiser } from '@/components/visualiser'
import { loadDataset } from '@/data/load'

export default async function Page() {
  const result = await loadDataset()
  if (!result.ok) return <LoadErrorScreen errors={result.errors} />
  return <Visualiser raw={result.data} />
}
