
const Hero = ({ avatar, title, subtitle, buttonLabel, buttonLink }: HeroSectionProps) => {
  return (
    <Section
      className="bg-slate-900 text-white"
      id="hero"
      variant="dark"
    >
      <Container className="flex flex-col items-center justify-center h-screen">
        <img src={avatar}
          alt={avatar.alt_text}
          width={600}
          height={600}
          className="rounded-full"
         />
        <h1 className="text-3xl font-bold">{title}</h1>
        <p className="text-lg">{subtitle}</p>
        <Button
          className="bg-emerald-400 hover:bg-emerald-500 text-white"
          variant="primary"
        >
          {buttonLabel}
        </Button>
        <a href={buttonLink}>
          <a>
            <lucide icon="chevron-right" className="text-cyan-400" />
          </a>
        </a>
      </Container>
    </Section>
  );
};

export default Hero;