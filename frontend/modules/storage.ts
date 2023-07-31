const dbName = "econox-core";
const objectStoreNames = ["setting", "general", "data"];
class ObjectStore {
    private name: string;
    private conn?: Promise<IDBDatabase>;

    constructor(name: string) {
        this.name = name;
    }

    private getConnection(): Promise<IDBDatabase> {
        return new Promise<IDBDatabase>((resolve, reject) => {
            const dbOpenRequest = indexedDB.open(dbName, 1); // 버전을 1로 고정
            dbOpenRequest.onupgradeneeded = (event) => {
                const database = (event.target as IDBOpenDBRequest).result;
                for (let storeName of objectStoreNames) {
                    if (!database.objectStoreNames.contains(storeName)) {
                        // 오브젝트 스토어가 없다면 생성합니다.
                        database.createObjectStore(storeName);
                    }
                }
            };
            dbOpenRequest.onsuccess = () => resolve(dbOpenRequest.result);
            dbOpenRequest.onerror = () => reject(dbOpenRequest.error);
        });
    }

    private async openStore(mode: IDBTransactionMode = "readwrite"): Promise<IDBObjectStore> {
        if (!this.conn) { // 커넥션 없으면 생성
            this.conn = this.getConnection();
        }
        try { // 커넥션 있으면 있는거 쓰기
            return (await this.conn).transaction(this.name, mode).objectStore(this.name);
        } catch (err) { // 있는거 안써지면 생성해서 쓰기
            this.conn = this.getConnection();
            return (await this.conn).transaction(this.name, mode).objectStore(this.name);
        }
    }

    /**
     * 객체를 저장합니다. key에 대한 객체가 이미 존재하면 덮어씌웁니다.
     * @param key - 저장할 객체에 대한 key
     * @param value - 저장할 객체
     */
    public async put(key: string, value: any): Promise<void> {
        const store = await this.openStore();
        return new Promise<void>((resolve, reject) => {
            const request = store.put(value, key);
            request.onsuccess = () => resolve();
            request.onerror = () => reject(request.error);
        });
    }

    /**
     * 객체를 가져옵니다. 대상 객체가 없으면 null을 반환합니다
     * @param key - 가져올 대상 객체 key
     * @returns key에 대한 객체
     */
    public async get(key: string): Promise<any | null> {
        const store = await this.openStore("readonly");
        return new Promise<any | null>((resolve, reject) => {
            const request = store.get(key);
            request.onsuccess = () => resolve(request.result || null);
            request.onerror = () => reject(request.error);
        });
    }

    /**
     * 객체를 삭제합니다. 대상 객체가 없으면 아무런 동작을 하지 않습니다.
     * @param key - 삭제할 대상 객체 key
     */
    public async delete(key: string): Promise<void> {
        const store = await this.openStore();
        return new Promise<void>((resolve, reject) => {
            const request = store.delete(key);
            request.onsuccess = () => resolve();
            request.onerror = () => reject(request.error);
        });
    }
}

// objectStoreNames로 사전 정의된 인스턴스만 생성 가능합니다.
export const settingObjectStore = new ObjectStore("setting");
export const generalObjectStore = new ObjectStore("general");
export const dataObjectStore = new ObjectStore("data");