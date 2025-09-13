declare module 'react' {
  interface StyleHTMLAttributes<T> extends React.HTMLAttributes<T> {
    jsx?: boolean
    global?: boolean
  }
}

declare module 'styled-jsx/style' {
  interface StyleProps {
    jsx?: boolean
    global?: boolean
  }
}