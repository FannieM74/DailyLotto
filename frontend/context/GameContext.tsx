"use client";
import { createContext, useContext, useState, ReactNode } from "react";

const GameContext = createContext<{
  game: string; setGame: (g: string) => void;
  method: string; setMethod: (m: string) => void;
}>({
  game: "daily_lotto",
  setGame: () => {},
  method: "all",
  setMethod: () => {},
});

export function GameProvider({ children }: { children: ReactNode }) {
  const [game, setGame] = useState("daily_lotto");
  const [method, setMethod] = useState("all");
  return <GameContext.Provider value={{ game, setGame, method, setMethod }}>{children}</GameContext.Provider>;
}

export function useGame() {
  return useContext(GameContext);
}
