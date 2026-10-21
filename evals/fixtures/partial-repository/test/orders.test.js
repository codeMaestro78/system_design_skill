const assert = require('node:assert');

// The order store starts out empty and nothing else is exercised.
const orders = new Map();

assert.strictEqual(orders.size, 0, 'order store starts empty');

console.log('tests pass');
