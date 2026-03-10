interface CarBodyDiagramProps {
  exterior: Record<string, string>;
  structural: Record<string, string>;
}

const DAMAGE_COLORS: Record<string, string> = {
  X: "#ef4444", // exchange - red
  W: "#f97316", // welding - orange
  A: "#eab308", // scratch - yellow
  U: "#f59e0b", // dent - amber
  C: "#a855f7", // corrosion - purple
  T: "#fb923c", // damage - red-orange
};

const DAMAGE_LABELS: Record<string, string> = {
  X: "Замена",
  W: "Сварка",
  A: "Царапина",
  U: "Вмятина",
  C: "Коррозия",
  T: "Повреждение",
};

// Zone positions for the top-view car diagram (approximate SVG coordinates)
// The car is 200x440 in the SVG viewBox
const ZONE_POSITIONS: Record<string, { x: number; y: number; w: number; h: number }> = {
  hood:             { x: 60,  y: 20,  w: 80, h: 60 },
  frontBumper:      { x: 60,  y: 0,   w: 80, h: 22 },
  frontFenderLeft:  { x: 10,  y: 40,  w: 48, h: 50 },
  frontFenderRight: { x: 142, y: 40,  w: 48, h: 50 },
  frontDoorLeft:    { x: 10,  y: 100, w: 48, h: 70 },
  frontDoorRight:   { x: 142, y: 100, w: 48, h: 70 },
  rearDoorLeft:     { x: 10,  y: 180, w: 48, h: 70 },
  rearDoorRight:    { x: 142, y: 180, w: 48, h: 70 },
  rearFenderLeft:   { x: 10,  y: 260, w: 48, h: 50 },
  rearFenderRight:  { x: 142, y: 260, w: 48, h: 50 },
  trunk:            { x: 60,  y: 320, w: 80, h: 60 },
  rearBumper:       { x: 60,  y: 378, w: 80, h: 22 },
  roofPanel:        { x: 60,  y: 140, w: 80, h: 120 },
  sideSkirtLeft:    { x: 0,   y: 130, w: 12, h: 140 },
  sideSkirtRight:   { x: 188, y: 130, w: 12, h: 140 },
  aPillarLeft:      { x: 10,  y: 85,  w: 48, h: 18 },
  aPillarRight:     { x: 142, y: 85,  w: 48, h: 18 },
  bPillarLeft:      { x: 10,  y: 166, w: 48, h: 18 },
  bPillarRight:     { x: 142, y: 166, w: 48, h: 18 },
};

function getZoneColor(zone: string, exterior: Record<string, string>, structural: Record<string, string>): string {
  // Structural damage takes priority
  const structDamage = structural[zone];
  if (structDamage && DAMAGE_COLORS[structDamage]) return DAMAGE_COLORS[structDamage];
  const extDamage = exterior[zone];
  if (extDamage && DAMAGE_COLORS[extDamage]) return DAMAGE_COLORS[extDamage];
  return "";
}

function getZoneDamageLabel(zone: string, exterior: Record<string, string>, structural: Record<string, string>): string {
  const structDamage = structural[zone];
  if (structDamage && DAMAGE_LABELS[structDamage]) return `${DAMAGE_LABELS[structDamage]} (каркас)`;
  const extDamage = exterior[zone];
  if (extDamage && DAMAGE_LABELS[extDamage]) return DAMAGE_LABELS[extDamage];
  return "";
}

export function CarBodyDiagram({ exterior, structural }: CarBodyDiagramProps) {
  const hasAnyDamage = Object.keys(exterior).length > 0 || Object.keys(structural).length > 0;

  // Collect unique damage types for legend
  const usedTypes = new Set<string>();
  for (const v of Object.values(exterior)) if (DAMAGE_LABELS[v]) usedTypes.add(v);
  for (const v of Object.values(structural)) if (DAMAGE_LABELS[v]) usedTypes.add(v);

  const defaultFill = "var(--color-bg-elevated)";

  return (
    <div>
      <div className="flex justify-center">
        <svg viewBox="0 0 200 400" className="h-auto w-full max-w-[240px]">
          {/* Car outline */}
          <path
            d="M100 8 C60 8 40 30 35 55 L30 90 C25 95 20 100 20 110 L15 165 L15 240 L20 295 C20 305 25 310 30 315 L35 350 C40 375 60 392 100 392 C140 392 160 375 165 350 L170 315 C175 310 180 305 180 295 L185 240 L185 165 L180 110 C180 100 175 95 170 90 L165 55 C160 30 140 8 100 8 Z"
            fill="none"
            stroke="var(--color-border)"
            strokeWidth="1.5"
          />
          {/* Windshield */}
          <path
            d="M50 82 L70 60 L130 60 L150 82 Z"
            fill="none"
            stroke="var(--color-border)"
            strokeWidth="1"
            opacity="0.5"
          />
          {/* Rear window */}
          <path
            d="M50 318 L70 340 L130 340 L150 318 Z"
            fill="none"
            stroke="var(--color-border)"
            strokeWidth="1"
            opacity="0.5"
          />

          {/* Zone rectangles */}
          {Object.entries(ZONE_POSITIONS).map(([zone, pos]) => {
            const color = getZoneColor(zone, exterior, structural);
            const label = getZoneDamageLabel(zone, exterior, structural);
            return (
              <g key={zone}>
                <rect
                  x={pos.x}
                  y={pos.y}
                  width={pos.w}
                  height={pos.h}
                  rx={3}
                  fill={color || defaultFill}
                  fillOpacity={color ? 0.35 : 0.15}
                  stroke={color || "var(--color-border)"}
                  strokeWidth={color ? 1.5 : 0.5}
                  strokeOpacity={color ? 0.8 : 0.3}
                />
                {color && (
                  <title>{label}</title>
                )}
              </g>
            );
          })}
        </svg>
      </div>

      {/* Legend */}
      {hasAnyDamage && usedTypes.size > 0 && (
        <div className="mt-3 flex flex-wrap justify-center gap-3">
          {Array.from(usedTypes).map((type) => (
            <div key={type} className="flex items-center gap-1.5 text-xs text-text-secondary">
              <span
                className="inline-block size-3 rounded-sm"
                style={{ backgroundColor: DAMAGE_COLORS[type], opacity: 0.7 }}
              />
              {DAMAGE_LABELS[type]}
            </div>
          ))}
        </div>
      )}
      {!hasAnyDamage && (
        <p className="mt-3 text-center text-xs text-text-secondary">
          Повреждения не обнаружены
        </p>
      )}
    </div>
  );
}
