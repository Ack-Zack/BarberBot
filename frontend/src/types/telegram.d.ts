export {}

declare global {
  interface Window {
    Telegram?: {
      WebApp?: {
        initData: string
        initDataUnsafe?: {
          start_param?: string
          user?: {
            id: number
            username?: string
            first_name: string
            last_name?: string
          }
        }
        ready?: () => void
        expand?: () => void
        close?: () => void
        showPopup?: (params: {
          title?: string
          message: string
          buttons?: { id?: string; type?: string; text?: string }[]
        }, callback?: (buttonId: string) => void) => void
        themeParams?: Record<string, string>
      }
    }
  }
}
