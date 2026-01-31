import gllmLogo from "@/assets/gLLM_Official.png"

export function Logo() {
  return (
    <div className="flex items-center gap-2">
      <img
        src={gllmLogo}
        alt="gLLM Logo"
        className="h-38 w-38 rounded-xl object-contain bg-background p-1"
      />
    </div>
  )
}
