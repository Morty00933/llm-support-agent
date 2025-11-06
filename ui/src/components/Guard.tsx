import { PropsWithChildren, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "@/store/auth";

export default function Guard({ children }: PropsWithChildren) {
  const { token } = useAuth();
  const nav = useNavigate();
  useEffect(() => {
    if (!token) nav("/login");
  }, [token]);
  return <>{children}</>;
}
