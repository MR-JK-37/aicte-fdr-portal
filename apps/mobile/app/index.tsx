// R0 boot shim: routes to the existing (still-mock, dark-theme) App shell so the bundle has
// real content to render while R0 proves the Expo Router boot path works end to end.
// R1 deletes the mocks; R2 adds real sign-in as the actual index route; R6 rebuilds the screens.
export { default } from '../App';
