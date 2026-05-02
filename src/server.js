import { createWebApplication } from './app.js';

const defaultPort = 3000;
const parsedPort = Number(process.env.PORT);
const port = Number.isFinite(parsedPort) ? parsedPort : defaultPort;
const webApplication = createWebApplication();

webApplication.listen(port, () => {
    console.log(`Match Predict Web app running at http://localhost:${port}`);
});