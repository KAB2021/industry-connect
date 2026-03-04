import { createBrowserRouter, RouterProvider } from 'react-router'
import AppLayout from './layouts/AppLayout'
import DashboardPage from './pages/DashboardPage'
import RecordsPage from './pages/RecordsPage'
import UploadPage from './pages/UploadPage'
import AnalysisPage from './pages/AnalysisPage'

const router = createBrowserRouter([
  {
    path: '/',
    element: <AppLayout />,
    children: [
      { index: true, element: <DashboardPage /> },
      { path: 'records', element: <RecordsPage /> },
      { path: 'upload', element: <UploadPage /> },
      { path: 'analysis', element: <AnalysisPage /> },
    ],
  },
])

export default function App() {
  return <RouterProvider router={router} />
}
