import * as React from 'react';

declare module 'react' {
  namespace JSX {
    interface IntrinsicElements {
      style: React.DetailedHTMLProps<React.StyleHTMLAttributes<HTMLStyleElement> & {
        jsx?: boolean;
        global?: boolean;
      }, HTMLStyleElement>;
    }
  }
}

declare module 'styled-jsx/style' {
  interface StyleProps {
    jsx?: boolean
    global?: boolean
  }
}