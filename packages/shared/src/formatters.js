/**
 * Indian currency & digit grouping formatters (SPEC / Stream R3 / R3.5).
 * Formats according to official Reserve Bank of India / Indian standards (Lakhs, Crores).
 */
export function formatINR(rupees, options) {
    return new Intl.NumberFormat('en-IN', {
        style: 'currency',
        currency: 'INR',
        minimumFractionDigits: options?.showPaisa ? 2 : 0,
        maximumFractionDigits: options?.showPaisa ? 2 : 0,
    }).format(rupees);
}
export function formatPaiseINR(paise, options) {
    return formatINR(paise / 100, options);
}
export function formatCroresINR(paise) {
    const crores = paise / 1000000000;
    return `₹${crores.toFixed(2)} Cr`;
}
export function formatLakhsINR(paise) {
    const lakhs = paise / 10000000;
    return `₹${lakhs.toFixed(2)} Lakh`;
}
export function formatNumberIN(num) {
    return new Intl.NumberFormat('en-IN').format(num);
}
