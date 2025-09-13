/// <reference types="react-scripts" />

declare namespace JSX {
  interface IntrinsicElements {
    style: React.DetailedHTMLProps<
      React.StyleHTMLAttributes<HTMLStyleElement> & {
        jsx?: boolean;
        global?: boolean;
      },
      HTMLStyleElement
    >;
  }
}
