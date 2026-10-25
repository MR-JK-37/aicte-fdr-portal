/**
 * Indian currency & digit grouping formatters (SPEC / Stream R3 / R3.5).
 * Formats according to official Reserve Bank of India / Indian standards (Lakhs, Crores).
 */
export declare function formatINR(rupees: number, options?: {
    showPaisa?: boolean;
}): string;
export declare function formatPaiseINR(paise: number, options?: {
    showPaisa?: boolean;
}): string;
export declare function formatCroresINR(paise: number): string;
export declare function formatLakhsINR(paise: number): string;
export declare function formatNumberIN(num: number): string;
