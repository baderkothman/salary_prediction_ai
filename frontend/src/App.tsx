import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Route, Routes } from "react-router-dom";

import { AppHeader } from "./components/AppHeader";
import { useLatestPublishedRun } from "./lib/queries";
import { ExplorePage } from "./pages/ExplorePage";
import { MethodologyPage } from "./pages/MethodologyPage";
import { OverviewPage } from "./pages/OverviewPage";
import { ResultDetailPage } from "./pages/ResultDetailPage";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 60_000,
      retry: 1,
    },
  },
});

function Shell() {
  const runQuery = useLatestPublishedRun();

  return (
    <>
      <AppHeader modelVersion={runQuery.data?.model_version} />
      <Routes>
        <Route path="/" element={<OverviewPage />} />
        <Route path="/explore" element={<ExplorePage />} />
        <Route path="/results/:id" element={<ResultDetailPage />} />
        <Route path="/methodology" element={<MethodologyPage />} />
      </Routes>
    </>
  );
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Shell />
      </BrowserRouter>
    </QueryClientProvider>
  );
}

export default App;
