import ResearchView from "../research-view";
import DailyContext from '../daily/context';
export default async function Page({params}: {params: Promise<{path:string[]}>}) {
  const path=(await params).path;
  return <><ResearchView path={path}/>{path[0]==='company'&&path.length===2&&<DailyContext symbol={path[1]}/>}</>;
}
