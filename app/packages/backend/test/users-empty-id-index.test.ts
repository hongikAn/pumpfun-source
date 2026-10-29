import test from 'node:test';
import assert from 'node:assert/strict';
import { UserStore } from '../src/users-store.js';
test('blank optional user IDs do not alias an arbitrary wallet-backed profile',()=>{
 const rows=new UserStore().list({}).slice(0,2);
 for(const row of rows)row.userId='';
 const store=new UserStore(rows,[rows[1].address]);
 assert.equal(store.getById(''),undefined);
 assert.equal(store.getOverview(''),undefined);
 assert.equal(store.isVerified(''),false);
 assert.deepEqual(store.batchVerified(['',rows[1].address]),{'':false,[rows[1].address]:true});
 const blankVerification=new UserStore(rows,['']);
 for(const row of rows)assert.equal(blankVerification.isVerified(row.address),false);
 for(const row of rows)assert.equal(store.getById(row.address)?.address,row.address);
});
