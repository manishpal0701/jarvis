import { useState, useEffect } from "react";
import { Link } from "next/link";
import { useSession, signIn, signOut } from "next-auth/react";

function Navbar() {
  const [session, setSession] = useSession();

  if (!session) {
    return (
      <nav>
        <ul>
          <li>
            <Link href="/login">Sign In</Link>
          </li>
          <li>
            <Link href="/signup">Sign Up</Link>
          </li>
        </ul>
      </nav>
    );
  }

  return (
    <nav>
      <ul>
        <li>
          <Link href="/">Home</Link>
        </li