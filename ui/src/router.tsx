import { createBrowserRouter, Navigate } from "react-router-dom";
import Layout from "@/components/Layout";
import Guard from "@/components/Guard";
import Login from "@/pages/Login";
import KB from "@/pages/KB";
import Tickets from "@/pages/Tickets";
import Agent from "@/pages/Agent";
import Settings from "@/pages/Settings";

export const router = createBrowserRouter([
  { path: "/login", element: <Login/> },
  {
    path: "/",
    element: <Guard><Layout/></Guard>,
    children: [
      { index: true, element: <Navigate to="kb" replace/> },
      { path: "kb", element: <KB/> },
      { path: "tickets", element: <Tickets/> },
      { path: "agent", element: <Agent/> },
      { path: "settings", element: <Settings/> }
    ]
  },
  { path: "*", element: <Navigate to="/" replace/> }
]);
