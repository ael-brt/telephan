interface LogoProps {
  size?: "sm" | "md" | "lg";
  showText?: boolean;
  className?: string;
}

export const Logo = ({ size = "md", showText = true, className = "" }: LogoProps) => {
  const sizes = {
    sm: { icon: 28, text: "text-lg" },
    md: { icon: 36, text: "text-xl" },
    lg: { icon: 48, text: "text-3xl" },
  };

  const { icon, text } = sizes[size];

  return (
    <div className={`flex items-center gap-2.5 ${className}`}>
      {/* Icon - Blue rounded square with T */}
      <svg
        width={icon}
        height={icon}
        viewBox="0 0 48 48"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
      >
        {/* Blue rounded rectangle background */}
        <rect
          x="2"
          y="2"
          width="44"
          height="44"
          rx="12"
          fill="hsl(210, 79%, 46%)"
        />
        {/* T shape */}
        <path
          d="M14 16C14 14.8954 14.8954 14 16 14H32C33.1046 14 34 14.8954 34 16V18C34 19.1046 33.1046 20 32 20H27V34C27 35.1046 26.1046 36 25 36H23C21.8954 36 21 35.1046 21 34V20H16C14.8954 20 14 19.1046 14 18V16Z"
          fill="white"
        />
      </svg>

      {/* Text */}
      {showText && (
        <span className={`font-semibold ${text} tracking-tight`}>
          <span className="text-[hsl(210,79%,46%)]">T</span>
          <span className="text-foreground">éléphan</span>
        </span>
      )}
    </div>
  );
};
