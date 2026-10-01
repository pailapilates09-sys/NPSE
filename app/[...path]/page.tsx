import ResearchView from "../research-view";
export default async function Page({params}: {params: Promise<{path:string[]}>}) {
  return <ResearchView path={(await params).path} />;
}
