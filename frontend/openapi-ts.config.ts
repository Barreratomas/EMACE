import { defineConfig } from '@hey-api/openapi-ts';

export default defineConfig({
  input: '../backend/openapi.json',
  output: 'src/lib/api/generated',
  plugins: [
    '@hey-api/client-axios',
    '@hey-api/typescript',
    {
      name: '@hey-api/sdk',
      transformer: true,
    },
    {
      name: '@hey-api/transformers',
      dates: true,
    },
  ],
});
