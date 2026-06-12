export const initSentinel = () => {
    const logToSentinel = (level, message, traceback = null) => {
        fetch("http://localhost:9999/log", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                source: "FRONTEND",
                level: level,
                message: message,
                traceback: traceback
            })
        }).catch(() => {}); // Prevent infinite loop if log server is down
    };

    // Store original functions to prevent dev-tools blackout
    const originalConsoleError = console.error;
    const originalConsoleWarn = console.warn;

    window.onerror = (message, source, lineno, colno, error) => {
        logToSentinel("ERROR", JS Error:  at ::, error?.stack);
    };

    window.onunhandledrejection = (event) => {
        logToSentinel("ERROR", Unhandled Promise Rejection: );
    };

    console.error = (...args) => {
        logToSentinel("ERROR", Console Error: );
        originalConsoleError.apply(console, args); // Maintain browser console output
    };
    
    console.warn = (...args) => {
        logToSentinel("WARNING", Console Warn: );
        originalConsoleWarn.apply(console, args);
    };
};
