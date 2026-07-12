"use client";
import GameSelector from "./GameSelector";
import MethodSelector from "./MethodSelector";
import { useGame } from "@/context/GameContext";

export default function SelectorBar() {
  const { game, setGame, method, setMethod } = useGame();
  return (
    <div className="selector-bar">
      <div className="selector-bar-inner">
        <div className="selector-row"><GameSelector value={game} onChange={setGame} /></div>
        <div className="selector-row"><MethodSelector value={method} onChange={setMethod} /></div>
      </div>
    </div>
  );
}
